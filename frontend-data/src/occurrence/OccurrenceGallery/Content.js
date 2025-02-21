import React from "react";

const Content = (props) => {
    const { galleryList } = props;

    // 如果 galleryList 不存在或為空，直接回傳提示訊息
    if (!galleryList || galleryList.length === 0) {
        return (
            <div className="occurrence_gallery_warning">
                當前篩選條件下沒有影像
            </div>
        );
    }

    return (
        <div className="occurrence_gallery">
            {galleryList.map((item, index) => (
                <a
                    key={index}
                    className="occurrence_gallery_item"
                    href={`/occurrence/${item.taibif_occurrence_id}`}
                >
                    <img
                        src={item.taibif_mediaReferences}
                        className="occurrence_gallery_item__image"
                    />
                    {item.taibif_scientificName && (
                        <div className="occurrence_gallery_item__name">
                            {item.taibif_scientificName}
                        </div>
                    )}
                </a>
            ))}
        </div>
    );
};

export default Content;
