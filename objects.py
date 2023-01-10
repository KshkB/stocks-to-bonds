from math import log

class Bond:

    def __init__(self, face, price, coupon, time):
        
        self.fv = face 
        self.price = price 
        self.coupon = coupon
        self.time = time

    def value(self):
        return -self.price + (1 + self.coupon * self.time)*self.fv

    def value_yield(self):
        return self.value()/self.price

    def yld(self):
        return self.coupon * self.fv/self.price

class Stock(Bond):

    def __init__(self, face, price, coupon, time, stock_price, earnings, div_yield):
        super().__init__(face, price, coupon, time)
        self.stock_price = stock_price
        self.earnings = earnings
        self.div_yield = div_yield

    def bond_time(self):

        time = self.time
        div_yld = self.div_yield
        bond_value = self.value_yield()

        if time == 0:
            rroi = 0
        if time == 1:
            rroi = bond_value - div_yld
        if time >= 2:
            binom = (1/2)*time*(time-1)
            a = binom 
            b = time + binom * div_yld
            c = time * div_yld - bond_value

            rroi = -b + (b**2 - 4 * a * c)**(1/2)
            rroi = rroi/(2*a)
        
        price_earnings = self.stock_price/self.earnings
        try:
            adj_time = log(1 + price_earnings * rroi)/log(1 + rroi)
        except ZeroDivisionError:
            adj_time = price_earnings

        excess = time - adj_time
        rsults = {
            'bond_adj_time': adj_time,
            'excess': excess
        }
        return rsults
