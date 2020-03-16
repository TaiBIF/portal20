import React from 'react';

class CTUpload extends React.Component {
  constructor(props) {
    super(props);
    this.state = {files:[], imagePreviewUrls:[]};
  }

  _handleSubmit(e) {
    e.preventDefault();
    // TODO: do something with -> this.state.file
    console.log('handle uploading-', this.state.files);
  }

  _handleImageChange(e) {
    e.preventDefault();
    const fs = [];
    for (let i of e.target.files) {
      fs.push(i);
    }
    this.setState({
      files: fs,
    });

    /*
    for (let i of e.target.files) {
      let reader = new FileReader();
      reader.onloadend = () => {
        let fs = this.state.files;
        let us = this.state.imagePreviewUrls;
        us.push(reader.result);
        fs.push(i);
        console.log
        this.setState({
          files: fs,
          imagePreviewUrls: us
        });
      }
      //reader.readAsDataURL(i);
    }
    */
  }

  render() {
    let {imagePreviewUrls} = this.state;
    let $imagePreview = null;
    if (imagePreviewUrls) {
      const xxx = imagePreviewUrls.map(function(x,i){
        return (<img key={i}  src={x} height="100"/>);
      });
      $imagePreview = (<div>{xxx}</div>);
    } else {
      $imagePreview = (<div className="previewText">Please select an Image for Preview</div>);
    }

    return (
      <div className="previewComponent">
        <form onSubmit={(e)=>this._handleSubmit(e)}>
          <input className="fileInput"
            type="file"
            multiple
            onChange={(e)=>this._handleImageChange(e)} />
          <button className="submitButton"
            type="submit"
            onClick={(e)=>this._handleSubmit(e)}>Upload Image</button>
        </form>
        <div className="imgPreview">
          {$imagePreview}
        </div>
      </div>
    )
  }
}
export default CTUpload;
