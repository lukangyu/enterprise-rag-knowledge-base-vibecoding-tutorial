package com.graphrag.gateway.proxy;

import com.graphrag.gateway.proxy.ProxyProperties;
import com.graphrag.gateway.proxy.ProxyService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Slf4j
@RestController
@RequiredArgsConstructor
public class ProxyController {
    
    private final ProxyService proxyService;
    private final ProxyProperties proxyProperties;
    
    @RequestMapping("/api/v1/search/**")
    public ResponseEntity<String> proxySearch(HttpServletRequest request, @RequestBody(required = false) String body) {
        return proxyService.forward("search", request, HttpMethod.valueOf(request.getMethod()), body);
    }
    
    @RequestMapping("/api/v1/kg/**")
    public ResponseEntity<String> proxyKg(HttpServletRequest request, @RequestBody(required = false) String body) {
        return proxyService.forward("kg", request, HttpMethod.valueOf(request.getMethod()), body);
    }
    
    @RequestMapping("/api/v1/qa/**")
    public ResponseEntity<String> proxyQa(HttpServletRequest request, @RequestBody(required = false) String body) {
        return proxyService.forward("qa", request, HttpMethod.valueOf(request.getMethod()), body);
    }
    
    @RequestMapping("/api/v1/document/**")
    public ResponseEntity<String> proxyDocument(HttpServletRequest request, @RequestBody(required = false) String body) {
        return proxyService.forward("document", request, HttpMethod.valueOf(request.getMethod()), body);
    }
    
    @GetMapping("/api/v1/proxy/routes")
    public Map<String, ProxyProperties.Route> getRoutes() {
        return proxyProperties.getRoutes();
    }
}
