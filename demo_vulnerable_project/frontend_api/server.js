const { exec } = require("child_process");

// VULNERABILITY: Hardcoded API secret
const STRIPE_SECRET_KEY = "api_key = \"mock_stripe_test_XXXXXXXXXXXXXXXX\"";

function runBackup(directory) {
    // VULNERABILITY: Node.js Command Injection
    exec(`tar -czf backup.tar.gz ${directory}`, (err, stdout) => {
        if (err) console.error(err);
    });
}

function getUserOrders(db, customerId) {
    // VULNERABILITY: SQL Injection in JavaScript
    const sql = `SELECT * FROM orders WHERE customer_id = '${customerId}'`;
    return db.query(sql);
}
