import React from "react";

const CursorPagination = ({ nextCursor, cursorHistory, onPageChange }) => {
    // 決定是否渲染上下一頁按鈕，並給各按鈕對應的 cursor
    return (
        <div className="cursor_btn_container">
            {cursorHistory.length > 0 && (
                <button
                    className="cursor_btn"
                    onClick={() => onPageChange("prev", null)}
                >
                    上一頁
                </button>
            )}
            {nextCursor && (
                <button
                    className="cursor_btn"
                    onClick={() => onPageChange("next", nextCursor)}
                >
                    下一頁
                </button>
            )}
        </div>
    );
};

export default CursorPagination;
