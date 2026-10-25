const API_URL = 'https://localhost:5000/books';
const form = document.getElementById('book-form');
const list = document.getElementById('book-list');

async function loadBooks(){
    const res = await fetch(API_URL);
    const books = await res.json();
    list.innerHTML = '';
    books.forEach(book => {
        const li = document.createElement('li');
        li.textContent = `${book.title} by ${book.author}`;
        list.appendChild(li);
    });
}

form.addEventListener('submit', async e => {   
    e.preventDefault();
    const title = document.getElementById('title').value;
    const author = document.getElementById('author').value;

    await fetch(API_URL, {
        method : 'POST',
        headers : {'Content-Type':'application/json'},
        body : JSON.stringify({title, author})
    });

    form.reset();
    loadBooks(); 

});

loadBooks();