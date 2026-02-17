package com.graphrag.document.constant;

public class TaskConstants {

    private TaskConstants() {
    }

    public static final String TASK_PROGRESS_KEY = "task:progress:";
    public static final String TASK_LOCK_KEY = "task:lock:";
    public static final String TASK_RETRY_KEY = "task:retry:";
    public static final String TASK_RETRY_PENDING_KEY = "task:retry:pending";
    public static final int MAX_RETRY_COUNT = 3;
}
