(define (make-interval a b)
  (cons a b))

(define (upper-bound x)
  (car x))

(define (lower-bound x)
  (cdr x))

(define (width x)
  (/
    (- (upper-bound x)
       (lower-bound x))
    2))

(define (add-interval x y)
  (make-interval
    (+ (lower-bound x) (lower-bound y))
    (+ (upper-bound x) (upper-bound y))))

(define (sub-interval x y)
  (add-interval
    x
    (make-interval
      (- (lower-bound y))
      (- (uppper-bound y)))))

; (define (mul-interval x y)
;   (let ((p1 (* (lower-bound x) (lower-bound y)))
;         (p2 (* (lower-bound x) (upper-bound y)))
;         (p3 (* (upper-bound x) (lower-bound y)))
;         (p4 (* (upper-bound x) (upper-bound y))))
;     (make-interval
;       (min p1 p2 p3 p4)
;       (max p1 p2 p3 p4))))
(define (mul-interval x y)
  (let ((lowerx (lower-bound x))
        (upperx (upper-bound x))
        (lowery (lower-bound y))
        (uppery (upper-bound y)))
    (cond
      ((and (<= uppperx 0) (<= uppery 0)) (make-interval ; x-- y--
                                            (* upperx uppery)
                                            (* lowerx lowery)))
      ((and (<= upperx 0) (< lowery 0) (>= uppery 0)) (make-interval ; x-- y-+
                                                         (* upperx uppery)
                                                         (* lowerx lowery)))
      ((and (<= upperx 0) (>= lowery 0)) (make-interval ; x-- y++
                                           (* lowerx uppery)
                                           (* upperx lowery)))
      ((and (<= lowerx 0) (> upperx 0) (<= uppery 0)) (make-interval ; x-+ y--
                                                        (* upperx lowery)
                                                        (* lowerx uppery)))
      ((and (<= lowerx 0) (> upperx 0) (>= lowery 0)) (make-interval ; x-+ y++
                                                        (* lowerx uppery)
                                                        (* upperx uppery)))
      ((and (>= lowerx 0) (<= uppery 0)) (make-interval ; x++ y--
                                           (* upperx uppery)
                                           (* lowerx lowery)))
      ((and (>= lowerx 0) (<= lowery 0) (> uppery 0)) (make-interval ; x++ y-+
                                                        (* upperx lowery)
                                                        (* upperx uppery)))
      ((and (>= lowerx 0) (>= lowery 0)) (make-interval ; x++ y++
                                           (* lowerx lowery)
                                           (* upperx uppery)))
      ((and (<= lowerx 0) (> upperx 0) (<= lowery 0) (> uppery 0)) ;x-+ y-+
       (let ((p1 (* lowerx lowery))
             (p2 (* lowerx uppery))
             (p3 (* upperx lowery))
             (p4 (* upperx uppery)))
         (make-interval
           (min p1 p2 p3 p4)
           (max p1 p2 p3 p4))))
      (else (error "logic error")))))

(define (div-interval x y)
  (if (= 0 (witdh y))
      (error "divisor witdh is zero")
      (mul-interval
        x
        (make-interval
          (/ 1 (upper-bound y))
          (/ 1 (lower-bound y))))))

(define (make-center-witdh c w)
  (make-interval
    (- c w)
    (+ c w)))

(define (center x)
  (/
    (+
      (lower-bound x)
      (upper-bound x))
    2))

(define (make-center-percent c p)
  (let ((w (* c p)))
    (make-center-width c w)))

(define (percent x)
  (/
    (width x)
    (center x)))
