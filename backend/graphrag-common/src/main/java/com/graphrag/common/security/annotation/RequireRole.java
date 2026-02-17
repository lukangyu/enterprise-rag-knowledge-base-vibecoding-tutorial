package com.graphrag.common.security.annotation;

import java.lang.annotation.*;

@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RequireRole {

    String[] value() default {};

    RequirePermission.Logical logical() default RequirePermission.Logical.AND;
}
