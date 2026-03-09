// POLYHEAL AI – Demo: Buggy Node.js file
// Bugs present:
//  1. Missing npm module (axios not installed)
//  2. ReferenceError: undefined variable
//  3. No error handling on async call

const axios = require('axios');  // ← Error if axios not installed

function getUserData(userId) {
    const url = `https://api.example.com/users/${userId}`;
    
    // Bug: no await, no error handling
    const response = axios.get(url);
    console.log(undeclaredVariable);  // ← ReferenceError!
    return response.data;
}

// Bug: calling with wrong type
getUserData(null);
