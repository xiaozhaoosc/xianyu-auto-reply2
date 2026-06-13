package com.xyun.platform.scheduler.job;

import com.xyun.platform.common.entity.XyDbBackupLog;
import com.xyun.platform.server.mapper.XyDbBackupLogMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jobrunr.jobs.annotations.Job;
import org.jobrunr.jobs.annotations.Recurring;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.zip.GZIPOutputStream;

/**
 * 数据库备份任务 — 每天凌晨2点执行
 * <p>
 * 执行 MySQL 数据库备份。逐表导出结构与数据，
 * 日志类表仅备份结构，写入 .sql.gz 压缩文件。
 * 自动清理超过10天的备份文件和日志记录。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DbBackupJob {

    /** 备份文件保留天数 */
    private static final int RETENTION_DAYS = 10;
    /** 每批读取的数据行数 */
    private static final int BATCH_SIZE = 1000;

    private final JdbcTemplate jdbcTemplate;
    private final XyDbBackupLogMapper logMapper;

    @Value("${spring.datasource.database:xy_platform}")
    private String database;

    @Value("${app.backup.dir:./backups}")
    private String backupDir;

    @Recurring(id = "db-backup-job", cron = "0 0 2 * * *")
    @Job(name = "数据库备份任务")
    public void execute() {
        log.info("[JobRunr] 数据库备份任务 开始执行");
        var startTime = System.currentTimeMillis();

        // 确保备份目录存在
        var backupPath = Path.of(backupDir);
        try {
            Files.createDirectories(backupPath);
        } catch (IOException e) {
            log.error("[JobRunr] 数据库备份任务 创建备份目录失败", e);
            writeLog("failed", null, null, null, 0, 0, 0, e.getMessage());
            throw new RuntimeException("创建备份目录失败", e);
        }

        var now = LocalDateTime.now();
        var fileName = String.format("backup_%s_%s.sql.gz", database,
            now.format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")));
        var filePath = backupPath.resolve(fileName);

        int tableCount = 0;
        long totalRows = 0;
        var errorMessages = new StringBuilder();

        try {
            // 1. 查询所有基础表
            var tables = jdbcTemplate.queryForList(
                "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_NAME",
                String.class, database
            );

            if (tables.isEmpty()) {
                log.warn("[JobRunr] 数据库备份任务 未查询到任何数据表，跳过备份");
            } else {
                log.info("[JobRunr] 数据库备份任务 共 {} 张表待备份", tables.size());

                // 2. 逐表导出
                try (var fos = Files.newOutputStream(filePath);
                     var gzos = new GZIPOutputStream(fos);
                     var writer = new BufferedWriter(new java.io.OutputStreamWriter(gzos))) {

                    writeHeader(writer, database, now);

                    for (int i = 0; i < tables.size(); i++) {
                        var table = tables.get(i);
                        try {
                            var rows = dumpTable(writer, table);
                            tableCount++;
                            totalRows += rows;
                            log.info("[JobRunr] 数据库备份任务 ({}/{}) 表 {} 完成，{} 行", i + 1, tables.size(), table, rows);
                        } catch (Exception e) {
                            var msg = "表 " + table + " 备份失败: " + e.getMessage();
                            log.error("[JobRunr] 数据库备份任务 {}", msg);
                            errorMessages.append(msg).append("; ");
                        }
                    }

                    writeFooter(writer);
                }
            }

            var fileSize = Files.exists(filePath) ? Files.size(filePath) : 0L;
            var durationMs = System.currentTimeMillis() - startTime;
            var status = errorMessages.isEmpty() ? "success" : "failed";

            writeLog(status, fileName, filePath.toString(), fileSize, tableCount, totalRows, (int) durationMs,
                errorMessages.isEmpty() ? null : errorMessages.toString());

            log.info("[JobRunr] 数据库备份任务 执行完成，状态: {}, 文件: {}, 表数: {}, 行数: {}, 大小: {} 字节, 耗时: {} ms",
                status, fileName, tableCount, totalRows, fileSize, durationMs);
        } catch (Exception e) {
            var durationMs = System.currentTimeMillis() - startTime;
            log.error("[JobRunr] 数据库备份任务 执行失败", e);

            // 清理不完整文件
            try { Files.deleteIfExists(filePath); } catch (Exception ignored) {}

            writeLog("failed", null, null, null, tableCount, totalRows, (int) durationMs, e.getMessage());
            throw new RuntimeException(e);
        } finally {
            // 清理过期备份
            cleanupExpiredBackups(backupPath);
        }
    }

    /** 写入备份文件头部 */
    private void writeHeader(BufferedWriter writer, String database, LocalDateTime now) throws IOException {
        writer.write("-- 数据库备份文件\n");
        writer.write("-- 数据库: " + database + "\n");
        writer.write("-- 备份时间(北京时间): " + now.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) + "\n");
        writer.write("-- 说明: 本文件由定时任务自动生成。普通表备份结构与数据，日志表仅备份结构\n\n");
        writer.write("SET NAMES utf8mb4;\n");
        writer.write("SET FOREIGN_KEY_CHECKS=0;\n\n");
    }

    /** 写入备份文件尾部 */
    private void writeFooter(BufferedWriter writer) throws IOException {
        writer.write("\nSET FOREIGN_KEY_CHECKS=1;\n");
    }

    /** 导出单张表，返回导出的数据行数 */
    private int dumpTable(BufferedWriter writer, String table) throws IOException {
        // 1. 表结构
        var createSql = jdbcTemplate.queryForObject(
            "SHOW CREATE TABLE `" + table + "`", (rs, rowNum) -> rs.getString(2)
        );
        writer.write("\n-- ----------------------------\n");
        writer.write("-- 表结构: " + table + "\n");
        writer.write("-- ----------------------------\n");
        writer.write("DROP TABLE IF EXISTS `" + table + "`;\n");
        writer.write(createSql + ";\n\n");

        // 日志类表仅备份结构
        if (isLogTable(table)) {
            writer.write("-- 表 " + table + " 为日志表，仅备份结构，跳过数据\n\n");
            return 0;
        }

        // 2. 表数据（分批查询）
        writer.write("-- 表数据: " + table + "\n");
        var columns = jdbcTemplate.queryForList(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
            String.class, table
        );
        var colClause = columns.stream().map(c -> "`" + c + "`").reduce((a, b) -> a + ", " + b).orElse("");

        int rowCount = 0;
        int offset = 0;
        while (true) {
            var rows = jdbcTemplate.queryForList(
                "SELECT * FROM `" + table + "` LIMIT ? OFFSET ?",
                BATCH_SIZE, offset
            );
            if (rows.isEmpty()) break;

            for (var row : rows) {
                var values = row.values().stream()
                    .map(this::formatValue)
                    .reduce((a, b) -> a + ", " + b)
                    .orElse("");
                writer.write("INSERT INTO `" + table + "` (" + colClause + ") VALUES (" + values + ");\n");
            }
            rowCount += rows.size();
            if (rows.size() < BATCH_SIZE) break;
            offset += BATCH_SIZE;
        }
        writer.write("\n");
        return rowCount;
    }

    /** 判断是否为日志类表 */
    private boolean isLogTable(String table) {
        var name = table.toLowerCase();
        return name.endsWith("_log") || name.endsWith("_logs");
    }

    /** 格式化SQL值 */
    private String formatValue(Object value) {
        if (value == null) return "NULL";
        if (value instanceof Boolean b) return b ? "1" : "0";
        if (value instanceof Number n) return n.toString();
        if (value instanceof LocalDateTime ldt) return "'" + ldt.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")) + "'";
        var text = value.toString()
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r");
        return "'" + text + "'";
    }

    /** 清理过期备份文件 */
    private void cleanupExpiredBackups(Path backupPath) {
        if (!Files.isDirectory(backupPath)) return;
        var cutoff = LocalDateTime.now().minusDays(RETENTION_DAYS);

        try (var stream = Files.list(backupPath)) {
            stream.filter(f -> f.getFileName().toString().startsWith("backup_") && f.getFileName().toString().endsWith(".sql.gz"))
                .filter(f -> {
                    try { return Files.getLastModifiedTime(f).toMillis() < cutoff.atZone(java.time.ZoneId.systemDefault()).toInstant().toEpochMilli(); }
                    catch (IOException e) { return false; }
                })
                .forEach(f -> {
                    try { Files.deleteIfExists(f); log.info("[JobRunr] 数据库备份任务 已清理过期备份文件: {}", f.getFileName()); }
                    catch (IOException e) { log.warn("[JobRunr] 数据库备份任务 删除过期备份文件失败: {}", f.getFileName(), e); }
                });
        } catch (IOException e) {
            log.error("[JobRunr] 数据库备份任务 清理过期备份文件异常", e);
        }

        // 清理过期日志记录
        try {
            var cutoffDate = LocalDateTime.now().minusDays(RETENTION_DAYS);
            logMapper.delete(
                new LambdaQueryWrapper<XyDbBackupLog>()
                    .lt(XyDbBackupLog::getCreatedAt, cutoffDate)
            );
        } catch (Exception e) {
            log.error("[JobRunr] 数据库备份任务 清理过期备份日志异常", e);
        }
    }

    /** 写入备份日志 */
    private void writeLog(String status, String fileName, String filePath, Long fileSize, int tableCount, long totalRows, int durationMs, String errorMessage) {
        try {
            var logRecord = new XyDbBackupLog();
            logRecord.setStatus(status);
            logRecord.setFileName(fileName);
            logRecord.setFilePath(filePath);
            logRecord.setFileSize(fileSize);
            logRecord.setTableCount(tableCount);
            logRecord.setTotalRows(totalRows);
            logRecord.setDurationMs(durationMs);
            logRecord.setErrorMessage(errorMessage != null && errorMessage.length() > 1000
                ? errorMessage.substring(0, 1000) : errorMessage);
            logMapper.insert(logRecord);
        } catch (Exception e) {
            log.error("[JobRunr] 数据库备份任务 记录备份日志失败", e);
        }
    }
}
