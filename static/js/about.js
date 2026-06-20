// Smooth scroll for navigation links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
      });
    }
  });
});

// Carousel functionality
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

    // Auto advance slides
    setInterval(() => this.nextSlide(), 5000);
  },

  updateSlide() {
    this.container.style.transform = `translateX(-${
      this.currentSlide * 33.333
    }%)`;

    // Update dots
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

// Initialize carousel
carousel.init();

// Add animation to CTA button
const ctaButton = document.getElementById("cta-button");
if (ctaButton) {
  ctaButton.addEventListener("click", () => {
    ctaButton.style.transform = "scale(0.95)";
    setTimeout(() => {
      ctaButton.style.transform = "scale(1)";
    }, 200);

    alert(
      "Thank you for your interest! This is where you would typically start your journey."
    );
  });
}

// Add intersection observer for fade-in animations
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1";
        entry.target.style.transform = "translateY(0)";
      }
    });
  },
  {
    threshold: 0.1,
  }
);

// Apply fade-in animation to feature cards
document.querySelectorAll(".feature-card").forEach((card) => {
  card.style.opacity = "0";
  card.style.transform = "translateY(20px)";
  card.style.transition = "opacity 0.5s ease, transform 0.5s ease";
  observer.observe(card);
});
