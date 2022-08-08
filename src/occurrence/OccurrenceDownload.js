import React,{useState,useEffect,useRef} from 'react';
import moment from 'moment'
import {fetchData, filtersToSearch} from '../Utils';
import {useWatch,useForm} from 'react-hook-form'
import { renderToString } from 'react-dom/server'

const filterLabels = {
  q:'關鍵字',
  year:'年份',
  month:'月份',
  dataset:'資料集',
  publisher:'發布單位',
  country:'國家',
  lat: '緯度',
  lng: '經度',
  taibif_county: '台灣縣市'
}

const API_URL_PREFIX = `/api/dataset/export`;

function OccurrenceDownload(props) {
  const {filters,menus} = props
  const [searchCondition,setSearchCondition] = useState('')
  const searchDate = moment().format('YYYY-MM-DD');
  const { register, handleSubmit, watch, setValue , formState: { errors } } = useForm();
  const email = useRef({});
  const expireDate = moment().add(1, 'Y').format('YYYY-MM-DD');
  email.current = watch("email");
  const count = props.data.count

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
    if(count > 1000000) {
      {  props.language === 'en' ?
      alert("File is too large to download, please contact us!")
      :alert("下載資料量過大，請聯絡窗口!")
      }
      return false
    }

    const facetQueryString = 'facet=year&facet=month&facet=dataset&facet=publisher&facet=country';
    
    const flQueryString = data.type == 'species' ? '&fl=scientificName,vernacularName,kingdom,phylum,class,order,family,genus,Total' : '';
    const queryString = `${facetQueryString}${flQueryString}&rows=1000000&wt=csv&type=${data.type}&email=${data.email}&search_condition=${encodeURIComponent(renderToString(searchCondition))}`;
  
    const apiURL = `${API_URL_PREFIX}`;
    const filterQueryString = filtersToSearch(filters)
    fetchData(filters ? `${apiURL}?${filterQueryString}&${queryString}` : `${apiURL}?${queryString}`)
    
    {  props.language === 'en' ?
    alert(`Download link has been sent to ${data.email}`)
    :alert(`下載資訊巳寄到${data.email}。`)
    }
    
  }

  return (
    <div className="col-xs-12">
    <div className="tools-intro-wrapper">
      {  props.language === 'en' ?
      <div className="tools-title">Download option</div>
    :<div className="tools-title">下載選項</div>}
        <div className="tools-content">
          <div className="table-responsive">
            <table className="table borderless text-left" id="occurence-charts-dataset-table">
              <tbody>
                <tr>
                  <th></th>
                  <th className='text-center'>Raw data<br/>(原始資料)</th>
                  <th className='text-center'>Interpreted data<br/>（TaiBIF 轉釋資料）</th>
                  <th className='text-center'>Coordinates<br/>（座標）</th>
                  <th className='text-center'>Format<br/>（檔案格式）</th>
                </tr>
                <tr>
                  <th>simple</th>
                  <td className='text-center'>o</td>
                  <td className='text-center'>o</td>
                  <td className='text-center'>o (if available)</td>
                  <td className='text-center'>csv</td>
                </tr>
                <tr>
                  <th>species list</th>
                  <td className='text-center'>x</td>
                  <td className='text-center'>o</td>
                  <td className='text-center'>x</td>
                  <td className='text-center'>csv</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <div className="tools-intro-wrapper">
      { props.language === 'en' ?
      <div className="tools-title">Download option</div>
    :<div className="tools-title">下載選項</div>}
        
          <div className="tools-content">
            <div className="table-responsive">
              <form onSubmit={handleSubmit(onSubmit)}>
                <input type='hidden' {...register('search_date')} value={searchDate}/>
                <table className="table borderless text-left" id="occurence-charts-dataset-table">
                  <tbody>
                  <tr>
                  { props.language === 'en' ?
                  <th>Download option: </th>
                  :<th>下載選項:</th>}
                    
                    <td>
                      <select  {...register("type",{required:true})}>
                        <option value='simple'>Simple</option>
                        <option value='species'>Species List</option>
                      </select>
                    </td>
                  </tr>
                  {/* <tr>
                    <th>搜尋條件:</th>
                    <td>{searchCondition}</td>
                  </tr> */}
                  { props.language == 'en' ?
                  <tr className='odd'>
                  <th>Search date:</th>
                  <td>{searchDate}</td>
                </tr>
                  :<tr className='odd'>
                  <th>搜尋時間:</th>
                  <td>{searchDate}</td>
                  </tr>
                  }
                  { props.language == 'en' ?
                  <tr>
                  <th>Terms of Use:</th>
                  <td>By downloading the material, you agreed to our<a target='_blank' href='/data-policy'> Terms of Use</a></td>
                </tr>
                  :<tr>
                  <th>使用條款:</th>
                  <td>請閱讀本站<a target='_blank' href='/data-policy'>使用條款</a>，下載資料即表示您同意該條款內容。</td>
                </tr>
                  }
                  
                  { props.language == 'en' ?
                  <tr className='odd'>
                  <th>Retention period:</th>
                  <td>This site retains the download file link for one year from {searchDate} to {expireDate}. <br/>Please <a target='_blank' href=' /contact-us'>contact us</a> for extensions or perpetual retention for publication</td>
                </tr>
                  :<tr className='odd'>
                  <th>保留期限:</th>
                  <td>本站保留下載檔案連結一年 {searchDate} 至 {expireDate}。<br/>如有延長需求或因學術出版引用而有永久保留需求，請<a target='_blank' href=' /contact-us'>聯絡我們</a></td>
                </tr>
                  }
                  
                  { props.language == 'en' ?
                  <tr>
                    <th>File format:</th>
                    <td>CSV</td>
                  </tr>
                  :
                  <tr>
                    <th>檔案格式:</th>
                    <td>CSV</td>
                  </tr>
                  }
                  { props.language == 'en' ?
                  <tr className='odd'>
                    <th>Note:</th>
                    <td>The file is generated offline. The system will send the download information to the email address you entered. <br/>If you did not received the email, please check your email settings or <a target='_blank' href=' /contact-us'>contact us</a></td>
                  </tr>
                  :
                  <tr className='odd'>
                    <th>備註:</th>
                    <td>檔案為離線產生，處理完成後，系統會寄下載資訊到您輸入的電子郵件信箱。<br/>如未收到信件，請檢查您的郵件設定，如仍未收到信件，請<a target='_blank' href=' /contact-us'>聯絡我們</a></td>
                  </tr>
                  }
                  
                  <tr>
                    <td colSpan={2}>
                      <div className="input-group">
                        <span className="input-group-addon">
                        
                        {props.language =='en' ?
                          <span className="input-group-text" id='download-email'>Email address</span>
                        :
                          <span className="input-group-text" id='download-email'>電子郵件信箱</span>
                        }
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
                        {props.language =='en' ?
                          <span className="input-group-text" id='confirm-download-email'>Re-enter email address</span>
                        :
                          <span className="input-group-text" id='confirm-download-email'>請再次輸入您的電子郵件信箱</span>
                        }
                        
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
                {props.language =='en' ?
                <button type='submit' className="btn text-center btn-block" id='download-dataset-btn'>Download</button>
                :
                <button type='submit' className="btn text-center btn-block" id='download-dataset-btn'>下載檔案</button>
                }
                
              </form>
            </div>
          </div>
        </div>
      </div>
  );
}
export {OccurrenceDownload, }

