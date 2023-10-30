window.__ready = function(fn){
  if (document.readyState !== 'loading') {
    fn();
  } else {
    document.addEventListener('DOMContentLoaded', fn);
  };
};

window.closeMobileMenu = function(){
  let d = document.getElementById('mobile-menu');
  console.log(d)
  d.classList.add('invisible', true);
  d.classList.remove('visible', true);
};

window.openMobileMenu = function(){
  let d = document.getElementById('mobile-menu');
  console.log(d)
  d.classList.remove('invisible', true);
  d.classList.add('visible', true);
};

window.__ready(()=>{
  document.getElementById('open-mobile-menu').addEventListener('click', window.openMobileMenu);
  Array.from(document.getElementsByClassName('close-mobile-menu')).forEach((x)=>{
    x.addEventListener('click', window.closeMobileMenu);
  })
});