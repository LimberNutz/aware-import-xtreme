-- Sample SQL queries for testing
SELECT * FROM files 
WHERE size > 1024 
  AND created_date >= '2025-01-01'
ORDER BY size DESC;

-- Find duplicate files
SELECT file_hash, COUNT(*) as duplicate_count
FROM files 
GROUP BY file_hash 
HAVING COUNT(*) > 1;

-- File type statistics
SELECT 
    SUBSTRING_INDEX(file_name, '.', -1) as extension,
    COUNT(*) as count,
    SUM(size) as total_size
FROM files 
GROUP BY extension 
ORDER BY count DESC;
