package com.graphrag.common.core.constant;

public class DocumentConstants {

    private DocumentConstants() {
    }

    public static final Long MAX_FILE_SIZE = 100 * 1024 * 1024L;
    public static final Long MAX_CHUNK_SIZE = 512L;
    public static final Integer DEFAULT_CHUNK_OVERLAP = 50;

    public static final String DOC_TYPE_PDF = "pdf";
    public static final String DOC_TYPE_WORD = "word";
    public static final String DOC_TYPE_MARKDOWN = "markdown";
    public static final String DOC_TYPE_TXT = "txt";
    public static final String DOC_TYPE_HTML = "html";

    public static final Integer STATUS_PENDING = 0;
    public static final Integer STATUS_PROCESSING = 1;
    public static final Integer STATUS_COMPLETED = 2;
    public static final Integer STATUS_FAILED = 3;

    public static final String STORAGE_LOCAL = "local";
    public static final String STORAGE_MINIO = "minio";
}
