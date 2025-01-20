var paletteSwitcher1 = document.getElementById("__palette_1");
var paletteSwitcher2 = document.getElementById("__palette_2");

paletteSwitcher1.addEventListener("change", function () {
  console.debug('change paletteSwitcher1=', paletteSwitcher1)
  location.reload();
});

paletteSwitcher2.addEventListener("change", function () {
  console.debug('change paletteSwitcher2=', paletteSwitcher2)
  location.reload();
});
