(load "4.scm")

(define (cond? exp) (tagged-list? exp 'cond))
(define (cond-clauses exp) (cdr exp))
(define (cond-else-clause? clause)
  (eq? (cond-predicate clause) 'else))
(define (cond-predicate clause) (car clause))
(define (cond-actions clause) (cdr clause))

; before
(define (cond->if exp)
  (expand-clauses (cond-clauses exp)))
(define (expand-clauses clauses)
  (if (null? clauses)
      'false
      (let ((first (car clauses))
            (rest (cdr clauses)))
        (if (cond-else-clause? first)
            (if (null? rest)
                (sequence->exp (cond-actions first))
                (error "ELSE clause isn't last -- COND->IF" clauses))
            (make-if (cond-predicate first)
                     (sequence->exp (cond-actions first))
                     (expand-clauses rest))))))

(define (last-exp? seq) (null? (cdr seq)))
(define (first-exp seq) (car seq))
(define (sequence->exp seq)
  (cond ((null? seq) seq)
        ((last-exp? seq) (first-exp seq))
        (else (make-begin seq))))
(define (make-begin seq) (cons 'begin seq))

(put 'cond 'eval (lambda (exp env)
                   (eval (cond->if (cons 'cond exp)) env)))

; after
(define (cond-map? clause)
  (eq? (cadr clause) '=>))
(define (cond-map-procedure clause)
  (caddr clause))
; the idea is that we need judge whether this clause is a cond-map
; (if (cond-map? clause)
;     (cond-map->if clause)
;     (ordinary-cond->if clause))

; (define (cond-map->if clause)
;   (make-if (cond-predicate clause)
;            (list (cond-map-procedure clause)
;                  (cond-predicate clause))
;            (expand-clauses rest)))

; but this will be ineffcient since we evaluate (cond-predicate clause) twice.
; to avoid this, we can use lambda to pass the predicate-value
(define (expand-clauses clauses)
  (if (null? clauses)
      'false
      (let ((first (car clauses))
            (rest (cdr clauses)))
        (if (cond-else-clause? first)
            (if (null? rest)
                (sequence->exp (cond-actions first))
                (error "ELSE clause isn't last -- COND->IF" clauses))
            (if (cond-map? first)
                (list
                  (make-lambda
                    '(predicate-value)
                    (list (make-if
                            'predicate-value
                            (list (cond-map-procedure first) 'predicate-value)
                            (expand-clauses rest))))
                  (cond-predicate first))
                (make-if (cond-predicate first)
                         (sequence->exp (cond-actions first))
                         (expand-clauses rest)))))))
