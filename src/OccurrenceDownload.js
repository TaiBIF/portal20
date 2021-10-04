import React,{useState,useEffect,useRef} from 'react';
import moment from 'moment'
import {fetchData, filtersToSearch} from '../Utils';
import {useWatch,useForm} from 'react-hook-form'
import { renderToString } from 'react-dom/server'
import process from "process"

const filterLabels = {
  q:'關鍵字',
  year:'年份',
  month:'月份',
  dataset:'資料集',
  publisher:'發布者',
  country:'國家',
}

const API_URL_PREFIX = `/api/dataset/export`;

function OccurrenceDownload(props) {
  const {filters,menus} = props
  const [filterTags,setFilterTags] = useState('')
  const [searchCondition,setSearchCondition] = useState('')
  const searchDate = moment().format('YYYY-MM-DD');
  const { register, handleSubmit, watch, setValue , formState: { errors } } = useForm();
  const email = useRef({});
  email.current = watch("email");

  useEffect(() => {
    generateFilterTag(filters,menus)
  },[filters])

  const generateFilterTag = (filters) => {
    let tags = [];
    for (let f of filters) {
      const menuKey = f.split('=');
  
        const data = tags?.[menuKey[0]] || []
        tags[[menuKey[0]]] = [...data,menuKey[1]].sort()
    }
  
    setFilterTags(tags)

    if(tags) {
      setSearchCondition(Object.keys(tags).map((key) => {
        return <div key={key}>
          {filterLabels[key]} : 
          {tags[key].map((item) => {
            return <span key={`${key}-${item}`}>{decodeURIComponent(item)}{key == 'month' ? '月' : ''} </span>
          })}
        </div>
      }))
    }
  }


  const onSubmit = (data) => {    
    const facetQueryString = 'facet=year&facet=month&facet=dataset&facet=publisher&facet=country';

    const apiURL = `${API_URL_PREFIX}`;
    console.log('data',data)
    filters.add(`email=${data.email}`);
    filters.add(`wt=csv`);
    filters.add(`fl=scientificName,vernacularName,kingdom,phylum,class,order,family,genus,species,Total`);

    filters.add(`search_condition=${encodeURIComponent(renderToString(searchCondition))}`);
    const queryString = filtersToSearch(filters)
    fetchData(filters ? `${apiURL}?${queryString}&${facetQueryString}` : `${apiURL}?${facetQueryString}`)
    
    filters.delete(`email=${data.email}`);
    filters.delete(`wt=csv`);
    filters.delete(`fl=scientificName,vernacularName,kingdom,phylum,class,order,family,genus,species,Total`);
    filters.delete(`search_condition=${encodeURIComponent(renderToString(searchCondition))}`);
    alert(`下載資訊巳寄到${data.email}。`)
  }

  return (
    <div className="col-xs-12">
      <div className="tools-intro-wrapper">
        <div className="tools-title">下載名錄</div>
          <div className="tools-content">
            <div className="table-responsive">
              <form onSubmit={handleSubmit(onSubmit)}>
                <input type='hidden' {...register('search_date')} value={searchDate}/>
                <table className="table borderless text-left" id="occurence-charts-dataset-table">
                  <tbody>
                  <tr>
                    <th>搜尋條件:</th>
                    <td>{searchCondition}</td>
                  </tr>
                  <tr className='odd'>
                    <th>搜尋時間:</th>
                    <td>{searchDate}</td>
                  </tr>
                  <tr>
                    <th>使用條款:</th>
                    <td>請閱讀本站<a target='_blank' href=''>使用條款</a>，下載資料即表示您同意該條款內容。</td>
                  </tr>
                  <tr className='odd'>
                    <th>保留期限:</th>
                    <td>本站保留下載檔案連結一年 (至)。<br/>如有延長需求或因學術出版引用而有永久保留需求，請<a href='#'>聯絡我們</a></td>
                  </tr>
                  <tr>
                    <th>檔案格式:</th>
                    <td>CSV</td>
                  </tr>
                  <tr className='odd'>
                    <th>備註:</th>
                    <td>檔案為離線產生，處理完成後，系統會寄下載資訊到您輸入的電子郵件信箱。<br/>如未收到信件，請檢查您的郵件設定，如仍未收到信件，請<a href='#'>聯絡我們</a></td>
                  </tr>
                  <tr>
                    <td colSpan={2}>
                      <div className="input-group">
                        <span className="input-group-addon">
                          <span className="input-group-text" id='download-email'>電子郵件信箱</span>
                        </span>	
                        <input type="email"  {...register("email",{required:true,
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i,
                          message: "Enter a valid e-mail address",
                        }})} className="form-control" name='email' aria-label="email" aria-describedby="download-email"/>
                      </div>
                      
                      {errors.email && <p>{errors.email.message}</p>}
                    </td>
                  </tr>
                  <tr>
                    <td colSpan={2}>
                      <div className="input-group">
                        <span className="input-group-addon">
                          <span className="input-group-text" id='confirm-download-email'>請再次輸入您的電子郵件信箱</span>
                        </span>	
                        <input type="email" className="form-control" {...register("confirm_email",{required:true,
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i,
                          message: "Enter a valid e-mail address",
                        },
                        validate: value => {
                            return value === email.current || "與電子郵件信箱不相同"
                        }})} aria-label="confirm email" aria-describedby="confirm-email"/>
                      </div>
                      {errors.confirm_email && <p className='text-danger'>{errors.confirm_email.message}</p>}
                    </td>
                  </tr>
                  </tbody>
                </table>
                <button type='submit' className="btn text-center btn-block" id='download-dataset-btn'>下載名目</button>
              </form>
            </div>
          </div>
        </div>
      </div>
  );
}
export {OccurrenceDownload, }
