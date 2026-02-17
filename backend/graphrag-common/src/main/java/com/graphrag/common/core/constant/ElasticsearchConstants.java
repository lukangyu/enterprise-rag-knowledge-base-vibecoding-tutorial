package com.graphrag.common.core.constant;

public final class ElasticsearchConstants {

    private ElasticsearchConstants() {
    }

    public static final String DOC_INDEX = "doc_index";

    public static final String METADATA_INDEX = "metadata_index";

    public static final int DEFAULT_SHARDS = 3;

    public static final int DEFAULT_REPLICAS = 1;

    public static final String FIELD_DOC_ID = "doc_id";

    public static final String FIELD_CHUNK_ID = "chunk_id";

    public static final String FIELD_CONTENT = "content";

    public static final String FIELD_TITLE = "title";

    public static final String FIELD_KEYWORDS = "keywords";

    public static final String FIELD_MILVUS_ID = "milvus_id";

    public static final String FIELD_METADATA = "metadata";

    public static final String FIELD_DOC_TYPE = "doc_type";

    public static final String FIELD_CATEGORY = "category";

    public static final String FIELD_TAGS = "tags";

    public static final String FIELD_CREATED_AT = "created_at";

    public static final int DEFAULT_TOP_K = 100;

    public static final int RRF_K = 60;

    public static final String ANALYZER_IK_SMART = "ik_smart";

    public static final String ANALYZER_IK_MAX_WORD = "ik_max_word";
}
