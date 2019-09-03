(load "70.scm")

(define (sum-of-cube p)
  (define (cube x)
    (* x x x))
  (+ (cube (car p))
     (cube (cadr p))))

(define ordered-number-by-cube-sum
  (weighted-pairs integers
                  integers
                  sum-of-cube))

(define ordered-number-by-cube-sum-verbose
  (stream-map (lambda (p) (cons (sum-of-cube p) p))
              ordered-number-by-cube-sum))

(define (make-ramanujan-filter)
  (let ((previous-sum-of-cube 0))
    (lambda (p)
      (let ((new-sum-of-cube (car p)))
        (if (= previous-sum-of-cube new-sum-of-cube)
            #t
            (begin (set! previous-sum-of-cube new-sum-of-cube)
                   #f))))))

(define ramanujan-numbers
  (stream-filter (make-ramanujan-filter)
                 ordered-number-by-cube-sum-verbose))
