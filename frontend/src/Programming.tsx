import React from "react";

const BG_IMAGE = "/underconstruction.jpg";

const containerStyle: React.CSSProperties = {
  flex: 1,
  width: "100%",
  height: "calc(100vh - 50px)", // Adjust 100px if your navbar is taller/shorter
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  color: "#232946",
  fontFamily: "Montserrat, Arial, sans-serif",
  background: `url(${BG_IMAGE}) center center / cover no-repeat`,
  margin: 0,
  padding: 0,
  boxSizing: "border-box",
  position: "relative",
  overflow: "hidden",
};

const overlayStyle: React.CSSProperties = {
  position: "absolute",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  background: "rgba(230, 234, 243, 0.2)", // lighter overlay for better image visibility
  zIndex: 1,
};

const textStyle: React.CSSProperties = {
  fontSize: "1.5rem",
  fontWeight: 600,
  textAlign: "center",
  maxWidth: "600px",
  lineHeight: 1.5,
  zIndex: 2,
};

const Programming: React.FC = () => (
  <div
    style={{
      flex: 1,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <div style={containerStyle}>
      <div style={overlayStyle}></div>
      <div style={textStyle}>
        Oops, page is under construction
        <br />
        Sorry, this page is still being built.
        <br />
        Please check back later!
      </div>
    </div>
  </div>
);

export default Programming;
