package com.readify.server.domain.notetask;

/**
 * 笔记任务状态枚举
 */
public enum NoteTaskStatus {
    /**
     * 待处理
     */
    PENDING("pending", "待处理"),
    
    /**
     * 处理中
     */
    PROCESSING("processing", "处理中"),
    
    /**
     * 已完成
     */
    COMPLETED("completed", "已完成"),
    
    /**
     * 失败
     */
    FAILED("failed", "失败");
    
    private final String code;
    private final String desc;
    
    NoteTaskStatus(String code, String desc) {
        this.code = code;
        this.desc = desc;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getDesc() {
        return desc;
    }
    
    /**
     * 根据code获取枚举
     *
     * @param code 状态码
     * @return 枚举
     */
    public static NoteTaskStatus getByCode(String code) {
        for (NoteTaskStatus status : NoteTaskStatus.values()) {
            if (status.getCode().equals(code)) {
                return status;
            }
        }
        return null;
    }
} 