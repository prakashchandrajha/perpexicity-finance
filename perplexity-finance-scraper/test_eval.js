const code = `(function(query) {
    return new Promise((resolve) => {
        resolve(query);
    });
})("hello\\nworld")`;
console.log(eval(code));
