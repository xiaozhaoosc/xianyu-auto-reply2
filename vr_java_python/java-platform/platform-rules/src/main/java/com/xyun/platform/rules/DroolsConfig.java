package com.xyun.platform.rules;

import org.kie.api.KieServices;
import org.kie.api.builder.KieBuilder;
import org.kie.api.builder.KieFileSystem;
import org.kie.api.runtime.KieContainer;
import org.kie.internal.io.ResourceFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;

import java.io.IOException;

/**
 * Drools 规则引擎配置 — 加载 classpath:rules/ 下所有规则文件
 */
@Configuration
public class DroolsConfig {

    private static final String RULES_PATH = "rules/";

    /**
     * 扫描规则文件并写入 KieFileSystem
     */
    @Bean
    public KieFileSystem kieFileSystem() throws IOException {
        var kieFileSystem = KieServices.Factory.get().newKieFileSystem();
        var resolver = new PathMatchingResourcePatternResolver();
        for (Resource resource : resolver.getResources("classpath*:" + RULES_PATH + "**/*.*")) {
            kieFileSystem.write(ResourceFactory.newClassPathResource(
                    RULES_PATH + resource.getFilename(), "UTF-8"));
        }
        return kieFileSystem;
    }

    /**
     * 构建 KieContainer，编译规则并校验
     */
    @Bean
    public KieContainer kieContainer() throws IOException {
        var ks = KieServices.Factory.get();
        var kieBuilder = ks.newKieBuilder(kieFileSystem());
        kieBuilder.buildAll();
        if (kieBuilder.getResults().hasMessages(org.kie.api.builder.Message.Level.ERROR)) {
            throw new RuntimeException("Drools 规则编译错误: " + kieBuilder.getResults());
        }
        return ks.newKieContainer(kieBuilder.getKieModule().getReleaseId());
    }
}
