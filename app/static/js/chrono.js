function updateChronos(){
document.querySelectorAll('.chrono').forEach(el=>{
const start = new Date(el.dataset.start);
const diff = Date.now() - start.getTime();
const days = Math.floor(diff / 86400000);
const hours = Math.floor((diff % 86400000)/3600000);
const minutes = Math.floor((diff % 3600000)/60000);
const seconds = Math.floor((diff % 60000)/1000);
el.textContent = `${days}j ${hours}h ${minutes}m ${seconds}s`;
});
}
setInterval(updateChronos, 1000); updateChronos();