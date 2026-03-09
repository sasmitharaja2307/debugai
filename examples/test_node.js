// ─────────────────────────────────────────────────────────────
// POLYHEAL AI – JavaScript Bug Examples  (Node.js)
// ─────────────────────────────────────────────────────────────

const axios = require('axios');  // Bug 1: Module not installed

// Bug 2: undefined variable
function greetUser() {
    console.log("Hello " + username);   // username is not defined
}

// Bug 3: async/await missing → unhandled Promise
function fetchData(url) {
    const result = axios.get(url);      // Returns Promise, not data
    console.log(result.data);           // undefined
}

// Bug 4: == instead of === (loose equality)
function isAdmin(role) {
    if (role == 1) {       // Should be ===
        return true;
    }
    return false;
}

// Bug 5: Off-by-one error
function getLastItem(arr) {
    return arr[arr.length];   // Should be arr.length - 1
}

// Bug 6: No error handling
async function saveUser(data) {
    const response = await axios.post('/api/users', data);
    return response.data;   // No try/catch — crashes on network error
}

// Run
greetUser();
