function toggleController(t,e,o){$(t+" > "+e).click(function(t){$(this).parent().find(o).slideToggle(),$(this).toggleClass("active")})}toggleController(".spoiler",".spoiler__header",".spoiler__content"),$(".wiki").MVisionToggleClass({classButton:"wiki__nav-item",toggleClassButton:"active",dataButtonAttr:"data-open-tab",classBox:"wiki__content",toggleClassBox:"active",dataBoxAttr:"data-name-tab",defaultElement:!0,defaultIndexElement:0,ancoreLinks:!0});
// On phones the tab list sits above the content: after picking a tab, scroll to the content.
$(document).on("click", ".wiki__nav-item", function () {
  var nav = document.querySelector(".wiki__nav"), box = document.querySelector(".wiki__box");
  if (!nav || !box || box.getBoundingClientRect().top < nav.getBoundingClientRect().bottom) return;
  setTimeout(function () { box.scrollIntoView({ behavior: "smooth", block: "start" }); }, 50);
});
