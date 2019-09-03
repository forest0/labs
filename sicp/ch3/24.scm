(define (make-table same-key?)
  (let ((table (list '*table*))
        (assoc-tolerance (association-procedure same-key? car)))

    (define (lookup key1 key2)
      (let ((subtable (assoc-tolerance key1 (cdr table))))
        (if subtable
            (let ((record (assoc-tolerance key2 (cdr subtable))))
              (if record
                  (cdr record)
                  #f))
            #f)))
    (define (insert! key1 key2 value)
      (let ((subtable (assoc-tolerance key1 (cdr table))))
        (if subtable
            (let ((record (assoc-tolerance key2 (cdr subtable))))
              (if record
                  (set-cdr! record value)
                  (set-cdr! subtable (cons (cons key2 value)
                                           (cdr subtable)))))
            (set-cdr! table (cons (list key1 (cons key2 value))
                                  (cdr table)))))
      'ok)
    (define (dispatch m)
      (cond ((eq? m 'lookup) lookup)
            ((eq? m 'insert!) insert!)
            (else (error "Unknown operation -- DISPATCH of table" m))))
    dispatch))

(define tolerance 0.1)
(define t (make-table (lambda (key given-key)
                        (and (<= key (+ given-key tolerance))
                             (>= key (- given-key tolerance))))))
