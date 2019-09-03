(define (empty-set? set)
  (null? set))

(define (element-of-set? x set)
  (cond ((empty-set? set) #f)
        ((equal? x (car set)) #t)
        (else
          (element-of-set? x (cdr set)))))

(define (adjoin-set x set)
  (if (element-of-set? x set)
      set
      (cons x set)))

(define (union-set set1 set2)
  (define (iter set result)
    (cond ((empty-set? set) result)
          ((element-of-set? (car set) result)
           (iter (cdr set) result))
          (else
            (iter (cdr set) (cons (car set) result)))))
  (iter set1 set2))
