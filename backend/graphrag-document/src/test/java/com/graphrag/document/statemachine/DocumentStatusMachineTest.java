package com.graphrag.document.statemachine;

import com.graphrag.document.enums.DocumentStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DocumentStatusMachineTest {

    private DocumentStatusMachine statusMachine;

    @BeforeEach
    void setUp() {
        statusMachine = new DocumentStatusMachine();
    }

    @Test
    @DisplayName("测试有效状态转换")
    void testCanTransition_ValidTransition() {
        assertTrue(statusMachine.canTransition(DocumentStatus.PENDING, DocumentStatus.PARSING));
        assertTrue(statusMachine.canTransition(DocumentStatus.PARSING, DocumentStatus.CHUNKING));
        assertTrue(statusMachine.canTransition(DocumentStatus.CHUNKING, DocumentStatus.EMBEDDING));
        assertTrue(statusMachine.canTransition(DocumentStatus.EMBEDDING, DocumentStatus.COMPLETED));
        assertTrue(statusMachine.canTransition(DocumentStatus.PARSING, DocumentStatus.FAILED));
        assertTrue(statusMachine.canTransition(DocumentStatus.CHUNKING, DocumentStatus.FAILED));
        assertTrue(statusMachine.canTransition(DocumentStatus.EMBEDDING, DocumentStatus.FAILED));
        assertTrue(statusMachine.canTransition(DocumentStatus.FAILED, DocumentStatus.PENDING));
    }

    @Test
    @DisplayName("测试无效状态转换")
    void testCanTransition_InvalidTransition() {
        assertFalse(statusMachine.canTransition(DocumentStatus.PENDING, DocumentStatus.COMPLETED));
        assertFalse(statusMachine.canTransition(DocumentStatus.PENDING, DocumentStatus.FAILED));
        assertFalse(statusMachine.canTransition(DocumentStatus.COMPLETED, DocumentStatus.PENDING));
        assertFalse(statusMachine.canTransition(DocumentStatus.COMPLETED, DocumentStatus.FAILED));
        assertFalse(statusMachine.canTransition(DocumentStatus.PARSING, DocumentStatus.PENDING));
        assertFalse(statusMachine.canTransition(DocumentStatus.CHUNKING, DocumentStatus.PARSING));
        assertFalse(statusMachine.canTransition(null, DocumentStatus.PARSING));
        assertFalse(statusMachine.canTransition(DocumentStatus.PENDING, null));
    }

    @Test
    @DisplayName("测试状态转换成功")
    void testTransition_Success() {
        DocumentStatus result = statusMachine.transition(DocumentStatus.PENDING, DocumentStatus.PARSING);
        assertEquals(DocumentStatus.PARSING, result);

        result = statusMachine.transition(DocumentStatus.PARSING, DocumentStatus.CHUNKING);
        assertEquals(DocumentStatus.CHUNKING, result);

        result = statusMachine.transition(DocumentStatus.CHUNKING, DocumentStatus.EMBEDDING);
        assertEquals(DocumentStatus.EMBEDDING, result);

        result = statusMachine.transition(DocumentStatus.EMBEDDING, DocumentStatus.COMPLETED);
        assertEquals(DocumentStatus.COMPLETED, result);
    }

    @Test
    @DisplayName("测试状态转换失败抛出异常")
    void testTransition_InvalidTransitionThrowsException() {
        assertThrows(IllegalStateException.class, () -> {
            statusMachine.transition(DocumentStatus.PENDING, DocumentStatus.COMPLETED);
        });

        assertThrows(IllegalStateException.class, () -> {
            statusMachine.transition(DocumentStatus.COMPLETED, DocumentStatus.PENDING);
        });
    }

    @Test
    @DisplayName("测试成功时获取下一个状态")
    void testGetNextStatus_Success() {
        assertEquals(DocumentStatus.PARSING, statusMachine.getNextStatus(DocumentStatus.PENDING, true));
        assertEquals(DocumentStatus.CHUNKING, statusMachine.getNextStatus(DocumentStatus.PARSING, true));
        assertEquals(DocumentStatus.EMBEDDING, statusMachine.getNextStatus(DocumentStatus.CHUNKING, true));
        assertEquals(DocumentStatus.COMPLETED, statusMachine.getNextStatus(DocumentStatus.EMBEDDING, true));
        assertNull(statusMachine.getNextStatus(DocumentStatus.COMPLETED, true));
        assertNull(statusMachine.getNextStatus(DocumentStatus.FAILED, true));
    }

    @Test
    @DisplayName("测试失败后获取下一个状态")
    void testGetNextStatus_Failure() {
        assertEquals(DocumentStatus.FAILED, statusMachine.getNextStatus(DocumentStatus.PENDING, false));
        assertEquals(DocumentStatus.FAILED, statusMachine.getNextStatus(DocumentStatus.PARSING, false));
        assertEquals(DocumentStatus.FAILED, statusMachine.getNextStatus(DocumentStatus.CHUNKING, false));
        assertEquals(DocumentStatus.FAILED, statusMachine.getNextStatus(DocumentStatus.EMBEDDING, false));
        assertNull(statusMachine.getNextStatus(DocumentStatus.COMPLETED, false));
        assertNull(statusMachine.getNextStatus(null, true));
        assertNull(statusMachine.getNextStatus(null, false));
    }
}
