import React from 'react';

class TaibifSearch extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      isLoaded: false
    }
  }
  componentDidMount() {
  let url = `${window.location.origin}/api/hotel_pricing/${this.props.slug}/`;
    fetch(url)
      .then(res => res.json())
      .then(
        (data) => {
          console.log('fetch', data);
          let values = {};
          this.setState({
            isLoaded: true,
          });
        },
        (error) => {
          this.setState({
            isLoaded: true,
            error
          });
        });
  }

  render() {
    const { error, isLoaded, data } = this.state;
    if (error) {
      return <div>Error: {error.message}</div>;
    } else if (!isLoaded) {
      return <div>Loading...</div>;
    }
    else {
      return (<h1>資料集a</h1>);
    }
  }
}

export default TaibifSearch;
