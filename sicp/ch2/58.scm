(define (variable? v)
  (symbol? v))

(define (same-variable? a b)
  (and (variable? a) (variable? b) (eq? a b)))

; change
(define (expression-type? sym)
  (lambda (exp)
    (and (pair? exp) (eq? (cadr exp) sym))))

(define sum? (expression-type? '+))

(define (=number? a b)
  (and (number? a) (number? b) (= a b)))

; change
(define (make-sum a b)
  (cond ((=number? a 0) b)
        ((=number? b 0) a)
        ((and (number? a) (number? b))
         (+ a b))
        (else
          (list a '+ b))))
; change
(define (addend exp)
  (car exp))

; change
(define (augend exp)
  (caddr exp))

(define product? (expression-type? '*))

; change
(define (make-product a b)
  (cond ((or (=number? a 0) (=number? b 0)) 0)
        ((=number? a 1) b)
        ((=number? b 1) a)
        ((and (number? a) (number? b)) (* a b))
        (else
          (list a '* b))))

; change
(define (multiplicand exp)
  (car exp))

; change
(define (multiplier exp)
  (caddr exp))

(define (deriv exp var)
  (cond ((number? exp) 0)
        ((variable? exp) (if (same-variable? exp var) 1 0))
        ((sum? exp) (make-sum (deriv (addend exp) var)
                              (deriv (augend exp) var)))
        ((product? exp)
         (make-sum
           (make-product (multiplier exp)
                         (deriv (multiplicand exp) var))
           (make-product (deriv (multiplier exp) var)
                         (multiplicand exp))))
        (else
          (error "unknown expression type: DERIV" exp))))
