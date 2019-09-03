(define (monte-carlo trials experiment)
  (define (iter trials-remaining trials-passed)
    (cond ((= trials-remaining 0)
           (/ trials-passed trials))
          ((experiment)
           (iter (- trials-remaining 1)
                 (+ 1 trials-passed)))
          (else
            (iter (- trials-remaining 1)
                  trials-passed))))
  (iter trials 0))

(define (random-in-range low high)
  (let ((range (- high low)))
    (+ low (random range))))

(define (estimate-integral P x1 x2 y1 y2 trials)
  (* (- y2 y1)
     (- x2 x1)
     (monte-carlo trials
                  (lambda ()
                    (let ((x (random-in-range x1 x2))
                          (y (random-in-range y1 y2)))
                      (P x y))))))

(define (estimate-pi trials)
  (define (square-distance x1 y1 x2 y2)
    (+ (square (- x1 x2))
       (square (- y1 y2))))
  (estimate-integral
    (lambda (x y)
      (< (square-distance x y 1 1) 1))
    0.0 2.0 0.0 2.0
    trials))

(exact->inexact (estimate-pi 100000))
