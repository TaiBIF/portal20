import React from 'react';

class DatasetTable extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      isLoaded: false,
    }
  }
 
  componentDidMount() {
    // handle if has query string
  }

  render() {
    const { error, isLoaded, data, serverError } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div className="search-loading"> 🌱 Searching... ⏳ </div>
    }  else if (serverError) {
      return `[server]: ${serverError}`; // should not shou this on production
    }
    else {
      return (<h1>table</h1>)
    }
  }
}

export default DatasetTable;
