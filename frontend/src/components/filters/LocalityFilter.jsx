import PropTypes from 'prop-types';
import { LOCALIDADES } from '../../utils/constants';

export function LocalityFilter({ value, onChange }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="px-3 py-2 border rounded-md">
      <option value="Todas">Todas</option>
      {LOCALIDADES.map(loc => <option key={loc} value={loc}>{loc}</option>)}
    </select>
  );
}
LocalityFilter.propTypes = { value: PropTypes.string, onChange: PropTypes.func };
export default LocalityFilter;


