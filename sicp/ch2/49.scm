(load "48.scm")

(define (segments->painter segment-list)
  (lambda (frame)
    (for-each
      (lambda (segment)
        (draw-line
          ((frame-coord-map frame)
           (start-segment segment))
          ((frame-coord-map frame)
           (end-segment segment))))
      segment-list)))

(define top-left (make-vect 0.0 0.0))
(define top-right (make-vect 1.0 0.0))
(define bottom-left (make-vect 0.0 1.0))
(define bottom-right (make-vect 1.0 1.0))


(define draw-outline
  (define top (make-segment top-left top-right))
  (define bottom (make-segment bottom-left bottom-right))
  (define left (make-segment top-left bottom-left))
  (define right (make-segment top-right bottom-right))

  (lambda (frame)
    (segments->painter (list top bottom left right))))

(define draw-X
  (define diagonal1 (make-segment top-left right-bottom))
  (define diagonal2 (make-segment bottom-left top-right))
  (lambda (frame)
    (segments->painter (list diagonal1 diagonal2))))

(define draw-diamond

  (define (middle v1 v2)
    (scale-vect
      0.5
      (add-vect v1 v2)))

  (define top-middle (middle top-left top-right))
  (define bottom-middle (middle bottom-left bottom-right))
  (define left-middle (middle top-left bottom-left))
  (define right-middle (middle top-right bottom-right))

  (define left-top-diamond (make-segment top-middle left-middle))
  (define right-top-diamond (make-segment top-middle right-middle))
  (define bottom-left-diamond (make-segment left-middle bottom-middle))
  (define bottom-right-diamond (make-segment bottom-middle right-middle))

  (lambda (frame)
    (segments->painter
      (list
        left-top-diamond
        right-top-diamond
        bottom-left-diamond
        bottom-right-diamond))))

(define wave
  (lambda (frame)
    (= todo never-do)))
