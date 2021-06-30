DROP TABLE [dbo].[audit_logs];
CREATE TABLE audit_logs (
    LoggedSeverity VARCHAR(54),
    LogTime DATETIME,
    MachineName VARCHAR (64),
    ProcessID INT,
    ProcessName VARCHAR(128),
    UserName    VARCHAR(128),
    UserID      VARCHAR(128),
    UserIP      VARCHAR(64),
    EventType   VARCHAR(64),
    ItemType    VARCHAR(64),
    ItemTypeFullName VARCHAR(128),
    ItemTitle   VARCHAR(64),
    CreatedOn  DATETIME DEFAULT CURRENT_TIMESTAMP    
);

CREATE INDEX ix_audit_logs_logtime on audit_logs(LogTime);