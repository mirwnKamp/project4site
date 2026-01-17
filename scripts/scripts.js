$(document).ready(function () {

  new Swiper(".mySwiper", {
    slidesPerView: 1,
    initialSlide: 1,
    spaceBetween: 40,
    keyboard: { enabled: true },
    pagination: {
      el: ".swiper-pagination",
      clickable: true
    },
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev"
    },
    breakpoints: {
      0: { spaceBetween: 20 },
      1024: { spaceBetween: 50 }
    }
  });

  const raceSwiper = new Swiper(".raceSwiper", {
    slidesPerView: "auto",
    spaceBetween: 12,
    freeMode: true,
    grabCursor: true,
    slidesOffsetBefore: 20,
    slidesOffsetAfter: 20,
    freeModeMomentum: true
  });

  // ✅ scroll στο active όταν φορτώνει
  setTimeout(() => {
    const activeBtn = document.querySelector(".race-btn.active");
    if (!activeBtn) return;

    const slide = activeBtn.closest(".swiper-slide");
    const index = [...slide.parentElement.children].indexOf(slide);

    // desktop → δεν χρειάζεται scroll
    if (raceSwiper.isLocked) return;

    raceSwiper.slideTo(index, 0);
  }, 0);

});
