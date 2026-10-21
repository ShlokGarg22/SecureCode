const { execFile } = require("child_process");

// REMEDIATED: Read from environment variable
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;

function runBackup(directory) {
    // REMEDIATED: execFile with argument array prevents command injection
    execFile("tar", ["-czf", "backup.tar.gz", directory], (err, stdout) => {
        if (err) console.error(err);
    });
}

function getUserOrders(db, customerId) {
    // REMEDIATED: Parameterized query placeholder
    const sql = "SELECT * FROM orders WHERE customer_id = ?";
    return db.query(sql, [customerId]);
}
