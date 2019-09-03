; "can be written as the sum of two squares in three different ways"
; which means >= 3?

(load "70.scm")

(define (sum-of-square p)
  (+ (square (car p))
     (square (cadr p))))

(define ordered-number-by-cube-sum
  (weighted-pairs integers
                  integers
                  sum-of-square))

; every item is (list (+ (square i) (square j))
;                     i
;                     j)
(define ordered-number-by-cube-sum-verbose
  (stream-map (lambda (p) (cons (sum-of-square p) p))
              ordered-number-by-cube-sum))

(define (make-the-filter)
  (let ((previous-sum 0)
        (repeat-cnt 0))
    (lambda (verbose-p)
      (if (= (car verbose-p) previous-sum)
          (begin (set! repeat-cnt (+ 1 repeat-cnt))
                 (>= repeat-cnt 2)) ; can be more
          (begin (set! repeat-cnt 0)
                 (set! previous-sum (car verbose-p))
                 #f)))))

(define sum-of-squares-in-at-least-three-way-verbose
  (stream-filter (make-the-filter)
                 ordered-number-by-cube-sum-verbose))

(define (merge-same items targets)
  (if (or (stream-null? items) (stream-null? targets))
      '()
      (let ((cur-one (stream-car items))
            (tar-one (stream-car targets)))
        (let ((cur-sum-of-square (car cur-one))
              (tar-sum-of-square (car tar-one)))
          (cond ((= cur-sum-of-square tar-sum-of-square) ; find one
                 (cons-stream cur-one
                              (merge-same (stream-cdr items) ; just forward items
                                          targets)))
                ((< cur-sum-of-square tar-sum-of-square)
                 (merge-same (stream-cdr items)
                             targets))
                (else (merge-same items (stream-cdr targets))))))))

(define sum-of-squares-in-at-least-three-way-very-verbose
  (merge-same
    ordered-number-by-cube-sum-verbose
    sum-of-squares-in-at-least-three-way-verbose))
