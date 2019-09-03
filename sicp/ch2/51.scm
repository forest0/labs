(define (below-v1 painter1 painter2)
  (let ((split-point (make-vect 0.0 0.5)))
    (let ((paint-bottom
            (transform-painter
              painter1
              (make-vect 0.0 0.0)
              (make-vect 1.0 0.0)
              split-point))
          (paint-top
            (transform-painter
              painter2
              split-point
              (make-vect 1.0 0.5)
              (make-vect 0.0 1.0))))
      (lambda (frame)
        (paint-bottom frame)
        (paint-top frame)))))

(define (below-v2 painter1 painter2)
  (let ((small1 ())
        (small2 (rotate270 painter2)))
    (lambda (frame)
      (ratate90
        (beside small1 small2)))))

(define (below-v2 painter1 painter2)
  (lambda (frame)
    (flip-horiz
      (rotate90
        (beside
          (rotate270
            (flip-horiz painter1))
          (rotate270
            (flip-horiz painter2)))))))
