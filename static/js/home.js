document.addEventListener("DOMContentLoaded", () => {
  // Smooth scroll
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });

  // Carousel
  const carousel = {
    container: document.querySelector(".carousel-container"),
    slides: document.querySelectorAll(".carousel-slide"),
    prevBtn: document.querySelector(".carousel-btn.prev"),
    nextBtn: document.querySelector(".carousel-btn.next"),
    dotsContainer: document.querySelector(".carousel-dots"),
    currentSlide: 0,
    slideCount: document.querySelectorAll(".carousel-slide").length,
    init() {
      // Create dots
      for (let i = 0; i < this.slideCount; i++) {
        const dot = document.createElement("div");
        dot.classList.add("dot");
        if (i === 0) dot.classList.add("active");
        dot.addEventListener("click", () => this.goToSlide(i));
        this.dotsContainer.appendChild(dot);
      }
      // Add button listeners
      this.prevBtn.addEventListener("click", () => this.prevSlide());
      this.nextBtn.addEventListener("click", () => this.nextSlide());
      // Auto advance
      setInterval(() => this.nextSlide(), 5000);
      this.updateSlide();
    },
    updateSlide() {
      const percentage = 100 / this.slideCount;
      this.container.style.transform = `translateX(-${
        this.currentSlide * percentage
      }%)`;

      document.querySelectorAll(".dot").forEach((dot, index) => {
        dot.classList.toggle("active", index === this.currentSlide);
      });
    },
    nextSlide() {
      this.currentSlide = (this.currentSlide + 1) % this.slideCount;
      this.updateSlide();
    },
    prevSlide() {
      this.currentSlide =
        (this.currentSlide - 1 + this.slideCount) % this.slideCount;
      this.updateSlide();
    },
    goToSlide(index) {
      this.currentSlide = index;
      this.updateSlide();
    },
  };

  carousel.init();


  // Fade-in animations
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll(".feature-card").forEach((card) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";
    card.style.transition = "opacity 0.5s ease, transform 0.5s ease";
    observer.observe(card);
  });
});
