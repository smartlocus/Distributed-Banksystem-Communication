namespace py stockportfolio

service StockPortfolioService {
    i32 RequestLoan(1: i32 amount) throws (1: string message),
    i32 ApproveLoan() throws (1: string message),
}

