create table if not exists alembic_version
(
    version_num varchar(32) not null
    primary key
    );

create table if not exists api_keys
(
    id          bigint auto_increment
    primary key,
    name        varchar(100)         not null,
    api_key     varchar(100)         not null,
    description varchar(500)         null,
    user_id     bigint               not null,
    enabled     tinyint(1) default 1 not null,
    create_time bigint               not null,
    update_time bigint               not null,
    constraint uk_key
    unique (api_key)
    )
    charset = utf8mb4;

create index idx_user_id
    on api_keys (user_id);

create table if not exists assistant_thinking
(
    id              bigint auto_increment comment '主键ID'
    primary key,
    project_id      bigint                             not null comment '工程ID',
    user_message_id bigint                             not null comment '对应的用户消息ID',
    content         longtext                           not null comment 'AI思考过程内容',
    created_at      datetime default CURRENT_TIMESTAMP not null comment '创建时间',
    updated_at      datetime default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '更新时间'
)
    comment 'AI助手思考过程表';

create index idx_created_at
    on assistant_thinking (created_at);

create index idx_project_id
    on assistant_thinking (project_id);

create index idx_user_message_id
    on assistant_thinking (user_message_id);

create table if not exists conversation_history
(
    id                     bigint unsigned auto_increment comment '主键ID'
    primary key,
    project_id             bigint                                     not null comment '工程ID',
    message_type           enum ('system', 'user', 'assistant')       not null comment '消息类型：系统消息/用户问题/AI思考过程/助手消息',
    content                longtext                                   not null comment '消息内容',
    priority               tinyint unsigned default '1'               not null comment '优先级：数值越大优先级越高，裁剪时优先保留',
    is_included_in_context tinyint(1)       default 1                 not null comment '是否包含在上下文中：0-不包含，1-包含',
    sequence               int unsigned     default '0'               not null comment '对话序号，同一会话中的排序',
    created_at             timestamp        default CURRENT_TIMESTAMP not null comment '创建时间',
    updated_at             timestamp        default CURRENT_TIMESTAMP not null on update CURRENT_TIMESTAMP comment '更新时间'
    )
    comment '对话历史记录表';

create index idx_created_at
    on conversation_history (created_at);

create index idx_message_type
    on conversation_history (message_type);

create index idx_project_session
    on conversation_history (project_id);

create index idx_session_sequence
    on conversation_history (sequence);

create table if not exists document
(
    id          bigint auto_increment comment '主键ID'
    primary key,
    file_id     bigint               not null comment '关联的文件ID',
    label       varchar(255)         not null,
    content     text                 not null comment '解析的文本内容',
    sequence    int                  not null comment '文档块序号',
    create_time bigint               not null comment '创建时间',
    update_time bigint               not null comment '更新时间',
    deleted     tinyint(1) default 0 not null comment '是否删除'
    )
    comment '文档解析内容表';

create index idx_document_file_id
    on document (file_id);

create table if not exists file
(
    id             bigint auto_increment comment '主键ID'
    primary key,
    original_name  varchar(255)                not null comment '原始文件名',
    storage_key    varchar(255)                not null comment '对象存储Key',
    storage_bucket varchar(100)                not null comment '对象存储桶',
    storage_type   varchar(20) default 'minio' not null comment '存储类型',
    size           bigint                      not null comment '文件大小(字节)',
    mime_type      varchar(100)                null comment '文件MIME类型',
    md5            char(32)                    null comment '文件MD5值',
    create_time    bigint                      not null comment '创建时间',
    update_time    bigint                      not null comment '更新时间',
    deleted        tinyint(1)  default 0       not null comment '是否删除',
    vectorized     tinyint(1)  default 0       not null comment '是否已向量化'
    )
    comment '文件表' charset = utf8mb4;

create index idx_md5
    on file (md5);

create table if not exists mind_map
(
    id          bigint auto_increment comment '思维导图ID'
    primary key,
    project_id  bigint               not null comment '工程id',
    file_id     bigint               not null,
    title       varchar(255)         not null comment '思维导图标题',
    type        varchar(10)          not null comment '笔记类型',
    description text                 null comment '思维导图描述',
    user_id     bigint               not null comment '创建者用户ID',
    created_at  bigint               not null comment '创建时间',
    updated_at  bigint               not null comment '更新时间',
    is_deleted  tinyint(1) default 0 not null comment '逻辑删除标记，0-未删除，1-已删除'
    )
    comment '思维导图主表' charset = utf8mb4;

create index idx_user_id
    on mind_map (user_id);

create table if not exists mind_map_node
(
    id           bigint auto_increment comment '节点唯一标识'
    primary key,
    project_id   bigint               null,
    mind_map_id  bigint               not null,
    file_id      bigint               not null comment '所属文件ID',
    parent_id    bigint               null comment '父节点ID，根节点为NULL',
    content      text                 null comment '节点内容',
    sequence     int        default 0 not null comment '同级节点间的排序顺序',
    level        int        default 0 not null comment '节点层级，根节点为0',
    created_time bigint               not null comment '创建时间',
    updated_time bigint               not null comment '更新时间',
    deleted      tinyint(1) default 0 not null comment '是否删除，0-未删除，1-已删除'
    )
    comment '思维导图节点表' charset = utf8mb4;

create index idx_file_id
    on mind_map_node (file_id);

create index idx_parent_id
    on mind_map_node (parent_id);

create index idx_sort
    on mind_map_node (file_id, parent_id, sequence);

create table if not exists note_task
(
    id          bigint auto_increment comment '主键ID'
    primary key,
    user_id     bigint               not null comment '用户ID',
    project_id  bigint               not null comment '关联项目ID',
    mind_map_id bigint               not null comment '关联的思维导图ID',
    file_id     bigint               not null comment '关联的文件ID',
    content     text                 not null comment '用户提问/任务内容',
    status      varchar(20)          not null comment '任务状态',
    result      text                 null comment '任务结果',
    create_time bigint               not null comment '创建时间',
    update_time bigint               not null comment '更新时间',
    deleted     tinyint(1) default 0 not null comment '是否删除'
    )
    comment '笔记任务表' charset = utf8mb4;

create index idx_note_task_create_time
    on note_task (create_time);

create index idx_note_task_project_id
    on note_task (project_id);

create index idx_note_task_status
    on note_task (status);

create index idx_note_task_user_id
    on note_task (user_id);

create table if not exists project_file
(
    id          bigint auto_increment comment '主键ID'
    primary key,
    project_id  bigint               not null comment '项目ID',
    user_id     bigint               null comment '用户id',
    file_id     bigint               not null comment '文件ID',
    create_time bigint               not null comment '创建时间',
    update_time bigint               not null comment '更新时间',
    deleted     tinyint(1) default 0 not null comment '是否删除'
    )
    comment '项目文件关联表' charset = utf8mb4;

create index idx_file_id
    on project_file (file_id);

create index idx_project_id
    on project_file (project_id);

create table if not exists repair_document
(
    id          int auto_increment
    primary key,
    file_id     int                  not null,
    content     text                 not null,
    sequence    int                  not null,
    create_time int                  not null,
    update_time int                  not null,
    deleted     tinyint(1) default 0 not null
    );

create table if not exists user
(
    id          bigint auto_increment comment '主键ID'
    primary key,
    username    varchar(50)          not null comment '用户名',
    password    varchar(100)         not null comment '密码',
    enabled     tinyint(1) default 1 not null comment '是否启用',
    create_time bigint               not null comment '创建时间',
    update_time bigint               not null comment '更新时间',
    deleted     tinyint(1) default 0 not null comment '是否删除'
    )
    comment '用户表' charset = utf8mb4;

create table if not exists project
(
    id          bigint auto_increment comment '主键ID'
    primary key,
    user_id     bigint               not null comment '用户ID',
    name        varchar(100)         not null comment '工程名称',
    description text                 null comment '工程描述',
    create_time bigint               not null comment '创建时间',
    update_time bigint               not null comment '更新时间',
    deleted     tinyint(1) default 0 not null comment '是否删除',
    constraint uk_name
    unique (name, deleted),
    constraint fk_project_user
    foreign key (user_id) references user (id)
    )
    comment '工程表' charset = utf8mb4;

create index idx_user_id
    on project (user_id);

