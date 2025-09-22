import PropTypes from 'prop-types';

export function Avatar({ name }) {
  const initial = (name || 'U').charAt(0).toUpperCase();
  return (
    <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
      {initial}
    </div>
  );
}
Avatar.propTypes = { name: PropTypes.string };
export default Avatar;


