package com.graphrag.document.service;

public interface DocumentProcessService {

    void processDocument(String docId);

    void parseDocument(String docId);

    void chunkDocument(String docId);

    void embedDocument(String docId);
}
