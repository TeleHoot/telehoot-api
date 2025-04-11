// Add as first line
try {
    const keyfileStatus = db.adminCommand({getCmdLineOpts: 1}).parsed.security.keyFile;
    if (keyfileStatus) print("Key file permissions OK");
} catch (e) {
    print(`Key file check failed: ${e}`);
    quit(1);
}
db.getSiblingDB('admin').auth('mongo', 'mongo');

rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: "mongo:27017" }
  ]
});

// Wait for replica set initialization
sleep(5000);

db.createUser({
  user: 'mongo',
  pwd: 'mongo',
  roles: [
    { role: 'root', db: 'admin' },
    { role: 'dbOwner', db: 'mongo' }
  ]
});