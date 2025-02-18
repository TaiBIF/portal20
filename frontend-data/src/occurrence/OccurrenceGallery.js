import React, { useEffect, useState } from "react";
import { fetchData, filtersToSearch } from "../Utils";
import Content from "./OccurrenceGallery/Content";
import CursorPagination from "./OccurrenceGallery/CursorPagination";

const OccurrenceGallery = (props) => {
    const { filters, navTabsRef } = props;
    const search = filtersToSearch(filters); // 把篩選條件轉換成 url 參數格式
    const API_URL_PREFIX = "/api/v1/occurrence/gallery";

    const [apiUrl, setApiUrl] = useState("");
    const [galleryList, setGalleryList] = useState([]);
    const [currentCursor, setcurrentCursor] = useState("");
    const [nextCursor, setNextCursor] = useState("");
    const [cursorHistory, setCursorHistory] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // 當篩選條件更新時，更新 URL
        const apiUrl = search ? `${API_URL_PREFIX}?${search}` : API_URL_PREFIX;
        setApiUrl(apiUrl);
        setCursorHistory([]); // 清空 curosr 紀錄
    }, [filters]);

    useEffect(() => {
        // 當 URL 更新時，重新 fetch 資料
        if (!apiUrl) return;
        setLoading(true);

        fetchData(apiUrl)
            .then((item) => {
                setLoading(false);
                setGalleryList(item.data);
                setcurrentCursor(item.current_cursor);
                setNextCursor(item.next_cursor);
            })
            .catch((error) => {
                setLoading(false);
                console.error("Fetch Error:", error);
            });
    }, [apiUrl]);

    const onPageChange = (direction, cursor) => {
        if (direction === "next") {
            setCursorHistory((prevHistory) => [...prevHistory, currentCursor]);
            setApiUrl(
                `${API_URL_PREFIX}?${search}&cursorMark=${encodeURIComponent(
                    cursor
                )}`
            );
        } else if (direction === "prev") {
            if (cursorHistory.length > 0) {
                const prevCursor = cursorHistory[cursorHistory.length - 1];
                setCursorHistory(cursorHistory.slice(0, -1));
                setApiUrl(
                    `${API_URL_PREFIX}?${search}&cursorMark=${encodeURIComponent(
                        prevCursor
                    )}`
                );
            }
        }

        if (navTabsRef.current) {
            navTabsRef.current.scrollIntoView({
                behavior: "smooth",
                block: "start",
            });
        }
    };

    return (
        <>
            {loading && (
                <div className="loader-container">
                    <div className="loader">
                        <div className="loader-wheel"></div>
                        <div className="loader-text"></div>
                    </div>
                </div>
            )}
            {!loading && (
                <>
                    <Content galleryList={galleryList} />
                    <CursorPagination
                        nextCursor={nextCursor}
                        cursorHistory={cursorHistory}
                        onPageChange={onPageChange}
                    />
                </>
            )}
        </>
    );
};

export default OccurrenceGallery;
