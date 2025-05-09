package com.readify.server.infrastructure.common;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "通用返回结果")
public class Result<T> {

    @Schema(description = "状态码", example = "200")
    private String code;

    @Schema(description = "提示信息", example = "操作成功")
    private String message;

    @Schema(description = "返回数据", nullable = true)
    private T data;

    public static Result<Void> success() {
        return success(null);
    }

    public static Result<Void> success(String message) {
        Result<Void> result = new Result<>();
        result.setCode("200");
        result.setMessage(message != null ? message : "操作成功");
        return result;
    }

    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode("200");
        result.setMessage("操作成功");
        result.setData(data);
        return result;
    }

    public static <T> Result<T> success(String message, T data) {
        Result<T> result = new Result<>();
        result.setCode("200");
        result.setMessage(message);
        result.setData(data);
        return result;
    }

    public static <T> Result<T> error(String code, String message) {
        Result<T> result = new Result<>();
        result.setCode(code);
        result.setMessage(message);
        return result;
    }

    public static <T> Result<T> error(String message) {
        return error("500", message);
    }
}