(define (install-syntax-cond eval-table)
  (define eval (eval-table 'get 'eval))
  (define make-if (eval-table 'get 'make-if))
  (define sequence->exp (eval-table 'get 'sequence->exp))
  (define make-lambda (eval-table 'get 'make-lambda))

  (define (cond-clauses exp) (cdr exp))
  (define (cond-else-clause? clause)
    (eq? (cond-predicate clause) 'else))
  (define (cond-predicate clause) (car clause))
  (define (cond-actions clause) (cdr clause))
  (define (cond->if exp) (expand-clauses (cond-clauses exp)))

  ; without cond-map support
  ;
  ; (define (expand-clauses clauses)
  ;   (if (null? clauses)
  ;       'false   ; no else clause
  ;       (let ((first (car clauses))
  ;             (rest (cdr clauses)))
  ;         (if (cond-else-clause? first)
  ;             (if (null? rest)
  ;                 (sequence->exp (cond-actions first))
  ;                 (error "ELSE clause isn't last: COND->IF"
  ;                        clauses))
  ;             (make-if (cond-predicate first)
  ;                      (sequence->exp (cond-actions first))
  ;                      (expand-clauses rest))))))

  ; add cond-map support
  ; clause syntax: (⟨test⟩ => ⟨recipient⟩)
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
                      (list 'predicate-value)
                      (list (make-if
                              'predicate-value
                              (list (cond-map-procedure first) 'predicate-value)
                              (expand-clauses rest))))
                    (cond-predicate first))
                  (make-if (cond-predicate first)
                           (sequence->exp (cond-actions first))
                           (expand-clauses rest)))))))

  (define (eval-cond exp env)
    (eval (cond->if exp) env))

  (eval-table 'put 'cond eval-cond)
  'done)
