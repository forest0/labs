(define (make-point x y)
  (cons x y))

(define (x-point p)
  (car p))

(define (y-point p)
  (cdr p))

(define (print-point p)
  (newline)
  (display "(")
  (display (x-point p))
  (display ",")
  (display (y-point p))
  (display ")"))
  (newline)

(define (make-segment start-point end-point)
  (cons start-point end-point))

(define (start-segment seg)
  (car seg))

(define (end-segment seg)
  (cdr seg))

(define (midpoint-segment seg)
  (define (average a b)
    (/ (+ a b) 2))
  (let ((s (start-segment seg))
        (e (end-segment seg)))
    (make-point
      (average (x-point s) (x-point e))
      (average (y-point s) (y-point e)))))



(define (make-rectangle left-top right-bottom)
  (make-segment left-top right-bottom))

(define (left-top rec)
  (start-segment rec))

(define (right-bottom rec)
  (end-segment rec))

; **************abstaction barrier*****************************

(define (width rec)
  (let ((lt (left-top rec))
        (rb (right-bottom rec)))
    (-
      (x-point rb)
      (x-point lt))))

(define (height rec)
  (let ((lt (left-top rec))
        (rb (right-bottom rec)))
    (-
      (y-point rb)
      (y-point lt))))

; **************abstaction barrier*****************************

(define (perimeter rec)
  (*
    2
    (+
      (width rec)
      (height rec))))

(define (area rec)
  (*
    (width rec)
    (height rec)))
