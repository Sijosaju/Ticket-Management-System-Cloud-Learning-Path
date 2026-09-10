const API = 'http://localhost:5000/api';
const token = () => localStorage.getItem('token');
const user = () => JSON.parse(localStorage.getItem('user') || 'null');
async function api(path, options={}) { const r=await fetch(API+path,{...options,headers:{'Content-Type':'application/json',...(token()?{Authorization:`Bearer ${token()}`}:{ }),...(options.headers||{})}}); const data=r.status===204?{}:await r.json(); if(!r.ok) throw Error(data.error||'Request failed'); return data; }
function nav(){ const u=user(); document.querySelector('#nav').innerHTML=`<b>Ticketly</b><a href="index.html">Home</a><a href="events.html">Events</a>${u?`<a href="bookings.html">My bookings</a>${u.role==='admin'?'<a href="admin.html">Admin</a>':''}<a href="#" onclick="logout()">Logout</a>`:'<a href="login.html">Login</a><a href="register.html">Register</a>'}` }
function logout(){localStorage.clear();location='index.html'} function showError(e){document.querySelector('#message').innerHTML=`<p class="notice">${e.message}</p>`}
function eventCard(e){return `<article class="card"><h3>${e.title}</h3><p class="muted">${e.category} · ${e.event_date} ${e.event_time}</p><p>${e.location}</p><a class="button" href="event-details.html?id=${e.id}">View event</a></article>`}
document.addEventListener('DOMContentLoaded',nav);
