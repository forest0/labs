(load "61.scm")

(define (div-series n-series d-series)
  (if (= 0 (stream-car d-series))
      (error "denominator has a zero constant term")
      (mul-series n-series
                  (invert-unit-series d-series))))

(define tangent-series (div-series sine-series cosine-series))
